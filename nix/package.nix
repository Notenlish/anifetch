{
  python3Packages,
  chafa,
  ffmpeg,
  lib,
  ...
}:
let
  fs = lib.fileset;
  sourceFiles = ../.;
in
fs.trace sourceFiles python3Packages.buildPythonApplication {
  name = "anifetch-wrapped";
  version = "git";
  pyproject = true;
  src = fs.toSource {
    root = ../.;
    fileset = sourceFiles;
  };

  build-system = with python3Packages; [
    setuptools
  ];

  dependencies = with python3Packages; [
    chafa
    ffmpeg
    platformdirs
    wcwidth
    rich
    pynput
  ];

  meta = with lib; {
    description = "neofetch but animated";
    homepage = "https://github.com/Notenlish/anifetch";
    license = licenses.mit;
    maintainers = with maintainers; [ Immelancholy ];
    mainProgram = "anifetch";
  };
}
