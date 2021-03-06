# These are Dell System IDs that predate a functional RBU implementation.

# blacklist specific versions
# (system_id, "bios_version")
dell_system_specific_bios_blacklist = [
    (0x0126, "a11"), # breaks usb keyboard in syslinux
    (0x01AD, "a11"), # breaks usb keyboard in syslinux
    (0x01BC, "a11"), # breaks usb keyboard in syslinux
    ( 0x022E, "a07"), # breaks wireless
]

dell_system_id_blacklist = [
    0x0092,
    0x0093,
    0x0094,
    0x0095,
    0x0096,
    0x0097,
    0x00B4,
    0x00BE,
    0x00C1,
    0x00C6,
    0x00C7,
    0x00D2,
    0x00D4,
    0x00D8,
    0x00E9,
    0x00F2,
    0x0108,
    0x010C,
    0x010D,
    0x010E,
    0x0110,
    0x0115,
    0x0116,
    0x0119,
    0x0132,
    0x0133,
    0x0144,
    0x0145,
    0x0147,
    0x014B,
    0x0126, # Optiplex GX620 - sometimes bricks. :(
    0x01AD, # Optiplex GX620 - sometimes bricks. :(
    0x01BC, # Optiplex GX620 - sometimes bricks. :(
    0x02a5, # R210 BIOS that incorrectly sets machine ID to T110 0x2a6
    0x02a6, # T110 BIOS, probably doesnt need to be blacklisted, but just in case
    ]
