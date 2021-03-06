import os
import stat
from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.errors import ConanInvalidConfiguration


class GmpConan(ConanFile):
    name = "gmp"
    description = "GMP is a free library for arbitrary precision arithmetic, operating on signed integers, rational numbers, and floating-point numbers."
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("conan", "gmp", "math")
    license = ("LGPL-3.0", "GPL-2.0")
    homepage = "https://gmplib.org"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "disable_assembly": [True, False],
               "run_checks": [True, False], "enable_cxx" : [True, False]}
    default_options = {"shared": False, "fPIC": True, "disable_assembly": True, "run_checks": False, "enable_cxx" : True}

    _source_subfolder = "source_subfolder"
    _autotools = None

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("The gmp package cannot be built on Visual Studio.")
        if self.options.shared:
            del self.options.fPIC
        if not self.options.enable_cxx:
            del self.settings.compiler.libcxx
            del self.settings.compiler.cppstd

    def package_id(self):
        del self.info.options.run_checks  # run_checks doesn't affect package's ID

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler != "Visual Studio" and \
           "CONAN_BASH_PATH" not in os.environ and tools.os_info.detect_windows_subsystem() != "msys2":
            self.build_requires("msys2/20200517")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("gmp-" + self.version, self._source_subfolder)

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            if self.settings.os == "Macos":
                configure_file = "configure"
                tools.replace_in_file(configure_file, r"-install_name \$rpath/", "-install_name ")
                configure_stats = os.stat(configure_file)
                os.chmod(configure_file, configure_stats.st_mode | stat.S_IEXEC)
            configure_args = []
            if self.options.disable_assembly:
                configure_args.append("--disable-assembly")
            if self.options.shared:
                configure_args.extend(["--enable-shared", "--disable-static"])
            else:
                configure_args.extend(["--disable-shared", "--enable-static"])
            if self.options.enable_cxx:
                configure_args.append("--enable-cxx")
            self._autotools.configure(args=configure_args)
        return self._autotools

    def build(self):
        with tools.chdir(self._source_subfolder):
            autotools = self._configure_autotools()
            autotools.make()
        # INFO: According to the gmp readme file, make check should not be omitted, but it causes timeouts on the CI server.
        if self.options.run_checks:
            autotools.make(args=["check"])

    def package(self):
        self.copy("COPYINGv2", dst="licenses", src=self._source_subfolder)
        self.copy("COPYING.LESSERv3", dst="licenses", src=self._source_subfolder)
        with tools.chdir(self._source_subfolder):
            autotools = self._configure_autotools()
            autotools.install()

        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "share"))
        os.unlink(os.path.join(self.package_folder, "lib", "libgmp.la"))
        if self.options.enable_cxx:
            os.unlink(os.path.join(self.package_folder, "lib", "libgmpxx.la"))

    def package_info(self):
        self.cpp_info.components["libgmp"].libs = ["gmp"]
        self.cpp_info.components["libgmp"].names["cmake_find_package"] = "GMP"
        self.cpp_info.components["libgmp"].names["cmake_find_package_multi"] = "GMP"
        self.cpp_info.components["libgmp"].names["pkg_config"] = "gmp"
        if self.options.enable_cxx:
            self.cpp_info.components["gmpxx"].libs = ["gmpxx"]
            self.cpp_info.components["gmpxx"].requires = ["libgmp"]
            self.cpp_info.components["gmpxx"].names["cmake_find_package"] = "GMPXX"
            self.cpp_info.components["gmpxx"].names["cmake_find_package_multi"] = "GMPXX"
            self.cpp_info.components["gmpxx"].names["pkg_config"] = "gmpxx"
