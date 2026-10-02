// 슬라이드 p10-v9-targetcond — 대상 형식 조건식, C# 9.0
using System;

class App
{
    static void Main(string[] args)
    {
        bool b = args.Length == 0;
        int? x = b ? 1 : null;               // int and <null>
        IComparable c = b ? 1 : "one";       // int and string
        Console.WriteLine(x + " " + c);
    }
}
