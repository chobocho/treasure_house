// 슬라이드 p10-v9-pat-vars — not·or 아래의 패턴 변수, C# 9.0
using System;

class App
{
    static int Len(object o)
    {
        if (o is not string s) return -1;
        return s.Length;          // s is definitely assigned here
    }

    static void Main()
    {
        Console.WriteLine(Len("four") + " " + Len(4));
#if BAD
        object o = 3;
        if (o is int i or long) Console.WriteLine(i);
        if (o is not int j) Console.WriteLine(j);
#endif
    }
}
