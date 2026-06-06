{
  description = "Neofetch but animated";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
      ...
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.callPackage ./nix/package.nix { };
          anifetch = self.packages.default;
        }
      );

      overlays = {
        default = final: _prev: {
          anifetch = import ./nix/package.nix final.pkgs;
        };
        anifetch = self.overlays.default;
      };

      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt-tree);

      devShell = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        pkgs.mkShell {
          packages = [
            self.packages.${pkgs.stdenv.hostPlatform.system}.default
          ];
        }
      );
    };
}
