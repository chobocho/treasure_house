// 슬라이드 p9-v8-nrt-bangbang — 매개변수의 !! 는 들어오지 않았다, C# 14
using System;

class App
{
    static int Len(string s!!) => s.Length;

    static void Main()
    {
        Console.WriteLine(Len("abc"));
    }
}
