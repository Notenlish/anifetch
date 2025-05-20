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
    devShells = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      default = pkgs.mkShell {
        packages = [
          (pkgs.python3.withPackages (python-pkgs: [
            python-pkgs.pillow
          ]))
          pkgs.neofetch
          pkgs.fastfetch
          pkgs.chafa
          pkgs.bc
          (pkgs.callPackage ./nix/packages/anifetch.nix {})
        ];
        shellHook = ''
        '';
      };
    });
  };
}
