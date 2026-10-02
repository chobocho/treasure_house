// 슬라이드 p8-v7_3-unmanaged — unmanaged 제약, C# 7.3
using System;

struct Pt
{
    public short X, Y;
    public Pt(short x, short y) { X = x; Y = y; }
}

class App
{
    static unsafe int Size<T>() where T : unmanaged
    {
        return sizeof(T);                    // needs unmanaged T
    }

    static unsafe string Bytes<T>(T value) where T : unmanaged
    {
        byte* p = (byte*)&value;             // a pointer to T
        var parts = new string[sizeof(T)];
        for (int i = 0; i < parts.Length; i++)
            parts[i] = p[i].ToString("X2");
        return string.Join(" ", parts);
    }

    static void Main()
    {
        Console.WriteLine(Size<int>() + " " + Size<Pt>() + " "
                          + Size<decimal>());
        Console.WriteLine(Bytes(0x01020304));
        Console.WriteLine(Bytes(new Pt(1, 2)));
        Console.WriteLine(BitConverter.IsLittleEndian);
    }
}
