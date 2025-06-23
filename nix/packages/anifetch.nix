{
  python3Packages,
  pkgs,
  lib,
  ...
}: let
  fs = lib.fileset;
  sourceFiles = ../../.;
in
  fs.trace sourceFiles
  python3Packages.buildPythonApplication {
    name = "aniftech-wrapped";
    version = "0.1.1";
    pyproject = true;
    src = fs.toSource {
      root = ../../.;
      fileset = sourceFiles;
    };

    build-system = [
      pkgs.python3Packages.setuptools
    ];

    dependencies = [
      pkgs.bc
      pkgs.chafa
      pkgs.ffmpeg
      pkgs.python3Packages.platformdirs
    ];

    meta = with lib; {
      description = "neofetch but animated ";
      homepage = "https://github.com/Notenlish/anifetch";
      license = licenses.mit;
      maintainers = with maintainers; [Immelancholy];
    };
  }
