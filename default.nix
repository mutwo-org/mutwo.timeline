let
  sourcesTarball = fetchTarball "https://github.com/mutwo-org/mutwo-nix/archive/refs/heads/main.tar.gz";
  mutwo-timeline = import (sourcesTarball + "/mutwo.core/default.nix") {};
  mutwo-timeline-local = mutwo-timeline.overrideAttrs (
    finalAttrs: previousAttrs: {
       src = ./.;
    }
  );
in
  mutwo-timeline-local

