// 슬라이드 p2-v1-concat — 문자열 + 는 왼쪽부터, C# 1.0
using System;

class App
{
    static void Main()
    {
        Console.WriteLine("a" + 1 + 2);          // "a1" + 2
        Console.WriteLine(1 + 2 + "a");          // 3 + "a"
        Console.WriteLine("a" + (1 + 2));
        Console.WriteLine('a' + 'b');            // int: 97 + 98
        Console.WriteLine("" + 'a' + 'b');
        string none = null;
        Console.WriteLine("[" + none + "]");     // null is ""
        object o = null;
        Console.WriteLine("[" + o + "]");
        Console.WriteLine(1.5 + "|" + true + "|" + 'c');
    }
}
