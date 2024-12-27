import binascii
import hashlib
import json
import os
import time

import bencode
import bitmath
from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.result import BODY_FORMAT, Result, ResultSection


class TorrentSlicer(ServiceBase):
    def __init__(self, config=None):
        super(TorrentSlicer, self).__init__(config)

    def start(self):
        self.log.debug("TorrentSlicer service started")

    # noinspection PyUnusedLocal
    @staticmethod
    def create_tables(infohash,
                      announce,
                      announce_list,
                      creation_date,
                      comment,
                      created_by,
                      encoding,
                      piece_length,
                      private,
                      name,
                      sflength,
                      sfmd5sum,
                      files,
                      piecehashes,
                      last_piece_size,
                      torrent_size,
                      torrent_type):
        """Create result tables for torrent metadata, information and pieces.

        Args:
            infohash: Infohash.
            announce: Announce list.
            creation_date: Creation date.
            comment: Comments.
            created_by: Created by Field.
            encoding: Encoding.
            piece_length: Piece length.
            private: Private.
            name: File name.
            sflength: Single file length.
            sfmd5sum: Single file md5.
            files: File list.
            piecehashes: Piece hashes,
            last_piece_size: Last piece size.
            torrent_size: Torrent size.
            torrent_type: Torrent type.

        Returns:
            Result dictionaries for torrent metadata, information and pieces.
        """
        announce_str = ""
        for x in announce_list:
            for y in x:
                announce_str += f"{y} "

        meta_dict = {
            'InfoHash:': infohash,
            'Announce:': announce,
            'Announce List*:': announce_str,
            'Creation Date*:': creation_date,
            'Comment*:': comment,
            'Created By*:': created_by,
            'Encoding*:': encoding,
            'Piece Length:': f"{str(piece_length)} ({bitmath.Byte(bytes=piece_length).best_prefix(system=bitmath.SI)})",
            'Private*:': private,
            'Name*:': name,
        }

        meta = []
        for k, i in sorted(meta_dict.items()):
            meta.append(f'{k:20s} {i}')

        cal_dict = {
            'Type of Torrent:': torrent_type,
            'Number of Pieces:': str(len(piecehashes)),
            'Last Piece Size:': f"{str(last_piece_size)} "
            f"({bitmath.Byte(bytes=last_piece_size).best_prefix(system=bitmath.SI)})",
            'Size of Torrent:': f"{str(torrent_size)} "
            f"({bitmath.Byte(bytes=torrent_size).best_prefix(system=bitmath.SI)})",
        }

        cal = []
        for k, i in sorted(cal_dict.items()):
            cal.append(f'{k:18s} {i}')

        des = []
        if len(files) > 0:
            des.append(f"{'File Path':100s} {'Length':10s} {'MD5Sum*':32s}")
            des.append(f"{'-' * 9:100s} {'-' * 6:10s} {'-' * 7:32s}")
            for f in files:
                fmd5 = ""
                path = ""
                for k, i in f.items():
                    if k == "hash":
                        fmd5 = i
                    if k == "path":
                        for x in i:
                            path = str(x)
                des.append(f"{path:100s} {bitmath.Byte(bytes=f['length']).best_prefix(system=bitmath.SI)} {fmd5:32s}")

        return meta, cal, des

    def run_tosl(self, filename, request):
        """Parse, extract and report on torrent file metadata using bencode.

        Args:
            filename: Path to torrent file.
            request: AL request object.

        Returns:
            None.
        """
        file_res = request.result

        torrent_file = open(filename, "rb").read()

        # noinspection PyBroadException
        try:
            metainfo = bencode.bdecode(torrent_file)
        except Exception:
            res = ResultSection("This is not a valid *.torrent file")
            file_res.add_section(res)
            return

        # Grab specific data from file

        announce = metainfo['announce']
        if 'announce-list' in metainfo:
            announce_list = metainfo['announce-list']
        else:
            announce_list = ""
        if 'creation date' in metainfo:
            creation_date = metainfo['creation date']
        else:
            creation_date = ""
        if 'comment' in metainfo:
            comment = metainfo['comment']
        else:
            comment = ""
        if 'created by' in metainfo:
            created_by = metainfo['created by']
        else:
            created_by = ""
        if 'encoding' in metainfo:
            encoding = metainfo['encoding']
        else:
            encoding = ""
        if 'url-list' in metainfo:
            url_list = metainfo['url-list']
        else:
            url_list = []

        info = metainfo['info']
        piece_length = info['piece length']
        pieces = info['pieces']
        if 'private' in info:
            private = info['private']
        else:
            private = ""
        if 'name' in info:
            name = info['name']
        else:
            name = ""
        if 'length' in info:
            sflength = info['length']
        else:
            sflength = ""
        if 'md5sum' in info:
            sfmd5sum = info['md5sum']
        else:
            sfmd5sum = ""
        if 'files' in info:
            files = info['files']
        else:
            files = []

        infohash = hashlib.sha1(bencode.bencode(info)).hexdigest()
        piecehashes = [binascii.hexlify(pieces[i:i+20]) for i in range(0, len(pieces), 20)]
        torrent_size = 0

        for i in files:
            torrent_size += i['length']
            i['length'] = i['length']
            for j in range(len(i['path'])):
                i['path'][j] = i['path'][j]

        if torrent_size == 0:
            torrent_type = 'single file torrent'
            torrent_size = sflength
        else:
            torrent_type = 'multiple file torrent'

        last_piece_size = min(torrent_size, (len(piecehashes) * int(piece_length)) - torrent_size)

        errmsg = []
        if last_piece_size > piece_length:
            errmsg.append("WARNING: The calculated length of the last piece is greater than the stated piece length")
        if (piece_length > torrent_size) and (torrent_type == 'multiple file torrent'):
            errmsg.append("WARNING: The stated length of an individual piece is greater "
                          "than the calculated torrent size")

        if creation_date != "":
            creation_date_conv = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(creation_date))
            creation_date_str = f"{str(creation_date)} ({creation_date_conv})"
        else:
            creation_date_str = creation_date

        # Generate result output
        meta, cal, des = self.create_tables(
            infohash,
            announce,
            announce_list,
            creation_date_str,
            comment,
            created_by,
            encoding,
            piece_length,
            private,
            name,
            sflength,
            sfmd5sum,
            files,
            piecehashes,
            last_piece_size,
            torrent_size,
            torrent_type
        )

        tosl_res = (ResultSection("Torrent File Details"))
        comment = "NOTE: '*' Denotes an optional field in the Torrent Descriptor File. As a result it may be blank. " \
                  "Refer to the BitTorrent Specification.\n"
        tosl_res.add_line(comment)

        if len(errmsg) > 0:
            error_res = (ResultSection("Errors Detected:", body_format=BODY_FORMAT.MEMORY_DUMP,
                                       parent=tosl_res))
            for line in errmsg:
                error_res.add_line(line)

        meta_res = (ResultSection("Meta Data:", body_format=BODY_FORMAT.MEMORY_DUMP,
                                  parent=tosl_res))
        for line in meta:
            meta_res.add_line(line)

        cal_res = (ResultSection("Calculated Data:", body_format=BODY_FORMAT.MEMORY_DUMP,
                                 parent=tosl_res))
        comment = "NOTE: the length of last piece is calculated as:" \
                  "(number of pieces X piece length) - size of torrent\n"
        cal_res.add_line(comment)
        for line in cal:
            cal_res.add_line(line)

        if len(des) > 0:
            des_res = (ResultSection("File paths:",
                                     body_format=BODY_FORMAT.MEMORY_DUMP, parent=tosl_res))
            for line in des:
                des_res.add_line(line)

        if url_list:
            url_res = (ResultSection("Urls found in metadata:", body_format=BODY_FORMAT.MEMORY_DUMP,
                                     parent=tosl_res))
            for url in url_list:
                url_res.add_line(url)
                url_res.add_tag('network.static.uri', url)

        sha1_hashes = os.path.join(self.working_directory, "hash_of_pieces.json")
        with open(sha1_hashes, "w") as sha1_file:
            # Decode byte hashes into strings
            json.dump([b.decode() for b in piecehashes], sha1_file)

        request.add_supplementary(sha1_hashes, "hash_of_pieces.json",
                                  "List of hashes in order of the different pieces of the torrent (json)")

        # Tags
        if len(announce) > 0:
            tosl_res.add_tag('network.static.uri', announce)

        for it in announce_list:
            for uri in it:
                tosl_res.add_tag('network.static.uri', uri)

        if name != "":
            tosl_res.add_tag('file.name.extracted', name)

        for f in files:
            for k, i in f.items():
                # if k == "hash" and len(k) > 0:
                #     tosl_res.add_tag(TAG_TYPE['FILE_MD5'], i)
                if k == "path" and len(k) > 0:
                    for x in i:
                        tosl_res.add_tag('file.name.extracted', str(x))

        file_res.add_section(tosl_res)

    def execute(self, request):
        """Main Module. See README for details."""
        request.result = Result()
        local_path = request.file_path
        self.run_tosl(local_path, request)
