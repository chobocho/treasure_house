// 슬라이드 p2-v1-explicit — 명시적 인터페이스 구현, C# 1.0
using System;

interface IPrinter { string Status(); }
interface IScanner { string Status(); }

class Combo : IPrinter, IScanner
{
    string IPrinter.Status() { return "printer: idle"; }
    string IScanner.Status() { return "scanner: busy"; }
    public string Status() { return "combo: ok"; }
}

class App
{
    static void Main()
    {
        Combo c = new Combo();
        Console.WriteLine(c.Status());
        Console.WriteLine(((IPrinter)c).Status());
        Console.WriteLine(((IScanner)c).Status());
        IScanner s = c;
        Console.WriteLine(s.Status());
    }
}
