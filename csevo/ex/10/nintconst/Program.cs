// 슬라이드 p10-v9-nint-const — nint 의 상수는 32비트 안에서만, C# 9.0
using System;

class App
{
    const nint Small = int.MaxValue;     // fits in 32 bits: a constant
    const nuint Big = uint.MaxValue;

    static void Main()
    {
        nint over = Small + 1;           // not a constant: run time
        Console.WriteLine(Small + " " + Big + " " + over);
#if BAD
        const nint c = Small + 1;
#endif
    }
}
