// 슬라이드 p5-v4-var-nested — 입력의 입력은 출력, C# 4.0
using System;

interface ISource<out T>
{
    void Each(Action<T> visit);         // T in an input of an input
    Func<T> Getter();                   // T in an output of an output
}

class Names : ISource<string>
{
    public void Each(Action<string> visit) { visit("a"); visit("b"); }
    public Func<string> Getter() { return delegate { return "g"; }; }
}

class Program
{
    static void Main()
    {
        ISource<object> src = new Names();
        src.Each(delegate(object o) { Console.Write(o + " "); });
        Console.WriteLine(src.Getter()());
    }
}
