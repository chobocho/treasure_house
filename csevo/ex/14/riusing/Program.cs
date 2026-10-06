// 슬라이드 p14-v13-ri-using — using·foreach 와 인터페이스, C# 13.0
using System;
using System.Collections;
using System.Collections.Generic;

ref struct Res : IDisposable
{
    void IDisposable.Dispose() => Console.WriteLine("Res disposed");
}

ref struct Three : IEnumerable<int>
{
    IEnumerator<int> IEnumerable<int>.GetEnumerator()
        => new List<int> { 1, 2, 3 }.GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => null;
}

interface IClose { void Dispose(); }   // not IDisposable

class App
{
    static void Use<T>(T t) where T : IDisposable, allows ref struct
    {
        using (t) { Console.WriteLine("in generic using"); }
    }
#if BAD
    static void Pat<T>(T t) where T : IClose, allows ref struct
    {
        using (t) { }                  // no pattern on T
    }
#endif

    static void Main()
    {
        using (new Res()) { Console.WriteLine("in using"); }
        Use(new Res());
        foreach (var x in new Three()) Console.Write(x);
        Console.WriteLine();
    }
}
