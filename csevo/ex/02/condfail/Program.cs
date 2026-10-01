// 슬라이드 p2-v1-condfail — 두 갈래의 형식이 맞아야 한다, C# 1.0
using System;

class App
{
    static void Main()
    {
        bool yes = true;
        string a = (yes ? 1 : null).ToString();      // int vs null
        string b = (yes ? 1 : "one").ToString();     // int vs string
        Console.WriteLine(a + " " + b);
    }
}
