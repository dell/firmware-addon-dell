#                                               -*- Autoconf -*-
# vim:tw=0:et:ts=4:sw=4
# Process this file with autoconf to produce a configure script.

####################################
# change version here.
AC_INIT([firmware-addon-dell],[2.2.0])

test -n "$RELEASE_MAJOR"      || RELEASE_MAJOR=2
test -n "$RELEASE_MINOR"      || RELEASE_MINOR=2
test -n "$RELEASE_MICRO"      || RELEASE_MICRO=1
test -n "$RELEASE_EXTRA"      || RELEASE_EXTRA=
####################################

AC_PREREQ(2.61)
AC_CONFIG_AUX_DIR([pkg])
AM_INIT_AUTOMAKE(1.9 tar-ustar no-define)
AM_MAINTAINER_MODE

# Checks for programs.
AC_PROG_INSTALL

# automake macros
AM_PATH_PYTHON

# Checks for header files.

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.

if test -z "$RELEASE_RPM_EXTRA"; then
    if test -z "$RELEASE_EXTRA"; then
        RELEASE_RPM_EXTRA=%{nil}
    else
        RELEASE_RPM_EXTRA=$RELEASE_EXTRA
    fi
fi

AC_SUBST([RELEASE_MAJOR])
AC_SUBST([RELEASE_MINOR])
AC_SUBST([RELEASE_MICRO])
AC_SUBST([RELEASE_EXTRA])
AC_SUBST([RELEASE_RPM_EXTRA])

# oddity: package name cannot contain '-', so we have to fix it
pkgpythondir=\${pythondir}/firmware_addon_dell
pkgpyexecdir=\${pyexecdir}/firmware_addon_dell

VERSION=[`echo ${RELEASE_MAJOR}.${RELEASE_MINOR}.${RELEASE_MICRO}${RELEASE_EXTRA}`]
PACKAGE_VERSION=$VERSION
PACKAGE_STRING=[`echo ${RELEASE_NAME}-${RELEASE_MAJOR}.${RELEASE_MINOR}.${RELEASE_MICRO}${RELEASE_EXTRA}`]
sed -i "s|(^#define PACKAGE_VERSION).*|\$1 \"$PACKAGE_VERSION\"|" confdefs.h
sed -i "s|(^#define PACKAGE_STRING).*|\$1 \"$PACKAGE_STRING\"|" confdefs.h

# generate files and exit
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([pkg/${PACKAGE_NAME}.spec])
AC_OUTPUT

