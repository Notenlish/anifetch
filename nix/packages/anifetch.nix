{
  python3Packages,
  pkgs,
  lib,
  ...
}: let
  # loop = pkgs.writeShellScriptBin "anifetch-static-resize2.sh" ''
  #   ${(builtins.readFile ../../src/anifetch/anifetch-static-resize2.sh)}
  # '';
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

    # TODO: need to add the platformdirs python dependency
    dependencies = [
      pkgs.bc
      pkgs.chafa
      pkgs.ffmpeg
      pkgs.python3Packages.platformdirs
      # loop
    ];
  }
