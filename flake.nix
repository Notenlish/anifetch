{
  description = "Neofetch but animated";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
    ...
  }: let
    inherit (self) outputs;
    systems = [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];
    forAllSystems = nixpkgs.lib.genAttrs systems;
  in {
    packages = forAllSystems (system: import ./nix/packages nixpkgs.legacyPackages.${system});

    overlays = import ./nix/overlays;

    formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.alejandra);

    devShell = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      myPython = pkgs.python3;
      pythonWithPkgs = myPython.withPackages (ps: [
        ps.pip
        ps.setuptools
      ]);
      venv = "venv";
    in
      pkgs.mkShell {
        packages = [
          pythonWithPkgs
          pkgs.bc
          pkgs.chafa
          pkgs.ffmpeg
        ];

        shellHook = ''
          if [ ! -d "${venv}" ]; then
            echo "Creating Python venv..."
            python3 -m venv ${venv}
          fi
          echo "Activating venv..."
          source ${venv}/bin/activate
        '';
      });
  };
}
