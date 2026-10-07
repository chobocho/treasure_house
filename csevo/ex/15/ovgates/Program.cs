// 슬라이드 p15-v14-gates-demo — 몸체 안의 C# 14 기능 셋, C# 14
using System;
using System.Collections.Generic;

delegate bool Parse(string s, out int n);

class Box { public int N; }

class Program
{
    static void Main()
    {
        Box box = new Box();
        box?.N = 5;                                 // ?.=
        string name = nameof(List<>);               // nameof(List<>)
        Parse p = (s, out n) => int.TryParse(s, out n); // out, no type
        p("7", out int seven);
        Console.WriteLine(box.N + " " + name + " " + seven);
    }
}
