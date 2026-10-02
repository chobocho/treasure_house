// 슬라이드 p9-v8-disp-foreach — foreach 도 Dispose 를 부른다, C# 8.0
using System;

ref struct RefIter
{
    int i;
    public int Current => i;
    public bool MoveNext() => ++i <= 2;
    public void Dispose() => Console.WriteLine("  RefIter.Dispose");
}

class ClassIter                      // Dispose, but no IDisposable
{
    int i;
    public int Current => i;
    public bool MoveNext() => ++i <= 2;
    public void Dispose() => Console.WriteLine("  ClassIter.Dispose");
}

class A { public RefIter GetEnumerator() => new RefIter(); }
class B { public ClassIter GetEnumerator() => new ClassIter(); }

class App
{
    static void Main()
    {
        foreach (int x in new A()) Console.WriteLine("A " + x);
        foreach (int x in new B()) Console.WriteLine("B " + x);
    }
}
