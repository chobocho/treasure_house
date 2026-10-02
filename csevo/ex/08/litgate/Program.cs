// 슬라이드 p8-v7-literals — 이진 리터럴과 자릿수 구분자, C# 7.0
using System;

[Flags]
enum Perm
{
    Read  = 0b0001,
    Write = 0b0010,
    Exec  = 0b0100,
    All   = 0b0111,
}

class App
{
    static void Main()
    {
        int mask = 0b1010_0101;
        int million = 1_000_000;
        long big = 0x7FFF_FFFF_FFFF_FFFF;
        double avogadro = 6.022_140_76e23;
        decimal price = 1_234.50m;

        Console.WriteLine(mask + " " + Convert.ToString(mask, 2));
        Console.WriteLine(million + " " + big);
        Console.WriteLine(avogadro.ToString("E8") + " " + price);
        Console.WriteLine(Perm.Read | Perm.Exec);
    }
}
