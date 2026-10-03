// 슬라이드 p12-v11-ur-user — 사용자 정의 >>>, C# 11.0
using System;

readonly struct Word
{
    public readonly short V;
    public Word(int v) => V = unchecked((short)v);
    // 16-bit logical shift: no promotion surprise for this type
    public static Word operator >>>(Word w, int n) =>
        new Word((ushort)w.V >> n);
    public static Word operator >>(Word w, int n) => new Word(w.V >> n);
}

class App
{
    static void Main()
    {
        Word w = new Word(-8);
        Console.WriteLine((w >> 1).V + " " + (w >>> 1).V);
        w >>>= 2;
        Console.WriteLine(w.V);
        Console.WriteLine(typeof(Word)
            .GetMethod("op_UnsignedRightShift").Name);
#if BAD
        Console.WriteLine(Word.op_UnsignedRightShift(w, 1).V);
#endif
    }
}
