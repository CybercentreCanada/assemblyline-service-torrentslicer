# TorrentSlicer Static Service

Extracts information from torrent files with the help of bencode.bdecode

### Information extracted

1.  Metadata:
    '*' Denotes an optional field in the Torrent Descriptor File. As a result it may be blank.
    Refer to the BitTorrent Specification.
        * InfoHash
        * Announce
        * Announce List*
        * Creation Date*
        * Comment*
        * Created By*
        * Encoding*
        * Piece Length
        * Private*
        * Name*

2.  Calculated Data:
        * Type of Torrent
        * Number of Pieces
        * Last Piece Size
        * Size of Torrent

3.  Files:
        *File Path
        *Length
        *MD5Sum

4. Url list (if found) in Metadata