
Recommended way to run the extract_hdr program is as follows:
    $ ./extract_hdr -o ~/biosmirror/ -r bios_spec.in -s systemid.conf

This will:
    1) Extract all hdr files to ~/biosmirror/hdr/
    2) create an RPM repository in ~/biosmirror/RPMS/
    3) give RPMS nice names as entered in systemid.conf


Both dosemu and unshield are used to extract Dell BIOS hdr files. 
Copies of the source used to build these are located here:
    http://linux.dell.com/libsmbios/download/tools/gpl_stuff/

