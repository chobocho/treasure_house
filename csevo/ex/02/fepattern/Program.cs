// 슬라이드 p2-v1_2-pattern — Dispose 가 불리는 조건, C# 1.2
using System;

class Bag                                  // pattern-based collection
{
    bool derived;
    public Bag(bool derived) { this.derived = derived; }
    public Cursor GetEnumerator()
    {
        return derived ? new DisposableCursor() : new Cursor();
    }
}

class Cursor                               // not sealed, no IDisposable
{
    int i;
    public bool MoveNext() { return ++i <= 1; }
    public int Current { get { return i; } }
    public void Dispose() { Console.WriteLine("  Cursor.Dispose"); }
}

class DisposableCursor : Cursor, IDisposable
{
    void IDisposable.Dispose() { Console.WriteLine("  IDisposable"); }
}

class App
{
    static void Main()
    {
        Console.WriteLine("Cursor:");
        foreach (int n in new Bag(false)) Console.WriteLine("  " + n);
        Console.WriteLine("DisposableCursor behind a Cursor type:");
        foreach (int n in new Bag(true)) Console.WriteLine("  " + n);
    }
}
