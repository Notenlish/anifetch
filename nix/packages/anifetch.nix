{
  python3Packages,
  pkgs,
  ...
}: let
  loop = pkgs.writeShellScriptBin "loop-anifetch.sh" ''
    ${(builtins.readFile ../../loop-anifetch.sh)}
  '';
  anifetch-unwrapped = pkgs.writers.writePython3Bin "anifetch.py" {doCheck = false;} (builtins.readFile ../../anifetch.py);
in
  python3Packages.buildPythonPackage {
    name = "aniftech-wrapped";
    src = anifetch-unwrapped;

    build-system = [
      pkgs.python3Packages.setuptools
    ];

    dependencies = [
      pkgs.bc
      pkgs.chafa
      pkgs.ffmpeg
      loop
    ];
    preBuild = ''
      cat > setup.py << EOF
      from setuptools import setup

      setup(
        name='anifetch',
        version='0.1.0',
        scripts=['bin/anifetch.py'],
      )
      EOF
    '';
    postInstall = ''
      mv $out/bin/anifetch.py $out/bin/anifetch
    '';
  }
