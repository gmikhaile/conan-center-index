import os.path
from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration


class CassandraCppDriverConan(ConanFile):
    name = "cassandra-cpp-driver"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://docs.datastax.com/en/developer/cpp-driver/"
    description = "DataStax C/C++ Driver for Apache Cassandra and DataStax Products"
    topics = ("cassandra", "cpp-driver", "database", "conan-recipe")

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "install_header_in_subdir": [True, False],
        "use_atomic": [None, "boost", "std"],
        "with_openssl": [True, False],
        "with_zlib": [True, False],
        "with_kerberos": [True, False],
        "use_timerfd": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "install_header_in_subdir": False,
        "use_atomic": None,
        "with_openssl": True,
        "with_zlib": True,
        "with_kerberos": False,
        "use_timerfd": True
    }

    generators = "cmake"
    exports_sources = [
        "CMakeLists.txt",
        "patches/*"
    ]

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["VERSION"] = self.version
        cmake.definitions["CASS_INSTALL_HEADER_IN_SUBDIR"] = self.options.install_header_in_subdir

        if self.options.use_atomic == "boost":
            # Compilation error on Linux with clang
            # cmake.definitions["CASS_USE_BOOST_ATOMIC"] = True
            # cmake.definitions["CASS_USE_STD_ATOMIC"] = False
            raise ConanInvalidConfiguration(
                "Boost.Atomic is not supported at the moment")
        elif self.options.use_atomic == "std":
            cmake.definitions["CASS_USE_BOOST_ATOMIC"] = False
            cmake.definitions["CASS_USE_STD_ATOMIC"] = True
        else:
            cmake.definitions["CASS_USE_BOOST_ATOMIC"] = False
            cmake.definitions["CASS_USE_STD_ATOMIC"] = False

            cmake.definitions["CASS_USE_OPENSSL"] = self.options.with_openssl
            cmake.definitions["CASS_USE_ZLIB"] = self.options.with_zlib

        if self.options.with_kerberos:
            # cmake.definitions["CASS_USE_KERBEROS"] = self.options.with_kerberos
            raise ConanInvalidConfiguration(
                "Kerberos is not supported at the moment")

        if self.settings.os == "Linux":
            cmake.definitions["CASS_USE_TIMERFD"] = self.options.use_timerfd

        cmake.configure()
        return cmake

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            del self.options.use_timerfd

    def requirements(self):
        self.requires("libuv/1.34.2")

        if self.options.with_openssl:
            self.requires("openssl/1.1.1g")

        if self.options.with_zlib:
            self.requires("zlib/1.2.11")

        if self.options.use_atomic == "boost":
            self.requires("boost/1.74.0")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("cpp-driver-{}".format(self.version), self._source_subfolder)

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        if not self.options.shared:
            self.cpp_info.defines.append("CASS_STATIC")
