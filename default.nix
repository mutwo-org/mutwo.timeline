with import <nixpkgs> {};
with pkgs.python310Packages;

let

  mutwo-core-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.core/archive/5817b4d233c0bf326a4709819a1e3a0e5f8595ca.tar.gz";
  mutwo-core = import (mutwo-core-archive + "/default.nix");

  python-ranges = pkgs.python310Packages.buildPythonPackage rec {
    name = "python-ranges";
    src = fetchFromGitHub {
      owner = "Superbird11";
      repo = "ranges";
      rev = "38ac789b61e1e33d1a8be999ca969f909bb652c0";
      sha256 = "sha256-oRQCtDBQnViNP6sJZU0NqFWkn2YpcIeGWmfx3Ne/n2c=";
    };
    # TypeError: calling <class 'ranges.RangeDict.RangeDict'> returned {}, not a test
    doCheck = false;
    checkInputs = [ python310Packages.pytest ];
  };

in

  buildPythonPackage rec {
    name = "mutwo.timeline";
    src = fetchFromGitHub {
      owner = "mutwo-org";
      repo = name;
      rev = "b6b0864a99f369043d69464e63d22796aeda3c79";
      sha256 = "sha256-jJaTgORcm61DUfePK5/pZ7MiZxCk1knen9ul7c9ZpfI=";
    };
    checkInputs = [
      python310Packages.pytest
    ];
    propagatedBuildInputs = [ 
      python310Packages.numpy
      mutwo-core
      python-ranges
    ];
    checkPhase = ''
      runHook preCheck
      pytest
      runHook postCheck
    '';
    doCheck = true;
  }
