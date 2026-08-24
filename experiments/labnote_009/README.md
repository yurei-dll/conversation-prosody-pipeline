# Labnote 009 native Kokoro stress pilot

**Status:** Implementation pending coordinated synthesis.

Labnote 008 proved that post-hoc token-local pitch editing can be audible while still
sounding layered and unnatural. This experiment removes DSP entirely and uses
Kokoro's documented Misaki stress representation before whole-utterance synthesis.

For two deterministically selected contrastive-emphasis pairs and both established
voices, each condition keeps ordinary primary stress on the intended focus word and
demotes the competing focus word with Misaki's `[word](-1)` annotation. `(+2)` is not
used because installed-version verification showed it is a no-op on content words
that already carry primary stress.

The runner fails before GPU synthesis unless the phoneme manifest proves that:

- both focus words have primary stress in ordinary G2P;
- each annotated condition changes its competing word from primary to secondary;
- the intended word remains byte-identical at the phoneme level; and
- no non-focus token phonemes change.

Audio is generated as a complete utterance by Kokoro. There is no segmentation,
splicing, pitch shifting, gain processing, time stretching, or crossfade stage.

