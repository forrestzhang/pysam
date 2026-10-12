import os
import subprocess
import sys
import threading
import errno

import pytest

from pysam import AlignmentFile
from TestUtils import make_data_files, BAM_DATADIR


def setUpModule():
    make_data_files(BAM_DATADIR)


def alignmentfile_writer_thread(infile, outfile):
    def _writer_thread(infile, outfile):
        """read from infile and write to outfile"""
        try:
            i = 0
            for record in infile:
                outfile.write(record)
                i += 1
        except IOError as e:
            if e.errno != errno.EPIPE:
                pass
        finally:
            outfile.close()

    writer = threading.Thread(target=_writer_thread, args=(infile, outfile))
    writer.daemon = True
    writer.start()
    return writer


class TestStream:

    def stream_process(self, proc, in_stream, out_stream, writer):
        with AlignmentFile(proc.stdout) as infile:
            read = 0
            for record in infile:
                read += 1
        return 0, read

    def test_text_processing(self):
        # D2-05 (Phase 2): the POSIX head utility does not exist on
        # Windows, so the pipe consumer is a small sys.executable -c
        # script (list form, no shell) that echoes exactly 200 lines and
        # exits - the test's purpose, a real subprocess consuming an fd
        # pipe, is unchanged.
        with subprocess.Popen(
                [sys.executable, "-c",
                 "import sys\n"
                 "for i, line in enumerate(sys.stdin):\n"
                 "    sys.stdout.write(line)\n"
                 "    if i >= 199:\n"
                 "        break\n"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE) as proc:

            in_stream = AlignmentFile(os.path.join(BAM_DATADIR, 'ex1.bam'))
            out_stream = AlignmentFile(
                proc.stdin, 'wh', header=in_stream.header)
            writer = alignmentfile_writer_thread(in_stream,
                                                 out_stream)

            written, read = self.stream_process(proc,
                                                in_stream,
                                                out_stream,
                                                writer)
            assert read == 198

    @pytest.mark.skip("test contains bug")
    def test_samtools_processing(self):
        # The following test causes the suite to hang
        # as the stream_processor raises:
        # ValueError: file has no sequences defined (mode='r') - is it SAM/BAM format?
        # The whole setup then hangs during exception handling.
        with subprocess.Popen('samtools view -b -f 4',
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              shell=True) as proc:

            in_stream = AlignmentFile(os.path.join(BAM_DATADIR, 'ex1.bam'))
            out_stream = AlignmentFile(
                proc.stdin, 'wb', header=in_stream.header)
            writer = alignmentfile_writer_thread(in_stream,
                                                 out_stream)

            written, read = self.stream_process(proc,
                                                in_stream,
                                                out_stream,
                                                writer)
            assert read == 35
