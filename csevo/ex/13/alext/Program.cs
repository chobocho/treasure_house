// 슬라이드 p13-v12-al-later — 별칭 이름 extension, C# 12.0
using System;
using extension = (int Lo, int Hi);

class App
{
    static void Main()
    {
        extension r = (1, 9);
        Console.WriteLine(r.Hi - r.Lo);
    }
}
