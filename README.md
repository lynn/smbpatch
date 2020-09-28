# smbpatch
Experiments in patching music into Super Mario Bros. 1

## What is this?
Some time in 2018, I had the idea to write my own soundtrack to [_Super Mario Bros._ for the NES](https://en.wikipedia.org/wiki/Super_Mario_Bros.) by hand-writing new sound data into the ROM.

This Python script is my progress: it expects a very legally obtained ([iNES format](https://wiki.nesdev.com/w/index.php/INES)) ROM file called `Super Mario Bros. (JU) (PRG0) [!].nes` in its working directory, and it will load that, patch a very short ditty into the overworld music, color the sky pink, and save it to `lynnsmb.nes`.

After learning how the sound engine works from some mysterious text files (I can't immediately find them anymore), I wrote some code that lets me program music for it in a "DSL" that looks kind of like the [ZZT `#play` command](https://apocalyptech.com/games/zzt/manual/langref.html#play):

```py
ow = overworld_pattern_list
self.rom[ow + 0] = \
    self.song('Overworld Intro', bpm150,
        melody('q E-4 F-4 G-4'),
        harmony('qC-4 qD-4 qE-4'),
        bass('q G-3 A-3 C-4'),
        noise('qK qK qO'))
```

For example, `q` means to set the note length to quarter notes, and `F-4` means to play an F in the fourth octave. These are simply mapped to byte instructions directly recognized by SMB's sound engine: `q` is `0x86`, and `F-4` is `0x36`.

You'll notice that the percussion and harmony have "length plus note"-style instructions (`qC-4` = `0x2C` plays a quarter-note C₄), whereas in the melody channel they're separate instructions. Strangely, that's just how the sound engine works. I suppose that this was the most compact way to store things.

Even this notation turned out to be pretty tedious to write by hand. There's an unused bit of code in there for parsing the music out of a [FamiTracker](http://famitracker.com/) module instead, so that I wouldn't need to write it by hand. But it seems I never got further than parsing a header. _Unless…_
