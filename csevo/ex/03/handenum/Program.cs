// 슬라이드 p3-v2-iterators-why — 손으로 쓴 열거자, C# 1.0
using System;
using System.Collections;

class Range : IEnumerable
{
    int start, count;

    public Range(int start, int count)
    {
        this.start = start;
        this.count = count;
    }

    public IEnumerator GetEnumerator() { return new Cursor(this); }

    class Cursor : IEnumerator           // the state lives here
    {
        Range r;
        int i = -1;
        public Cursor(Range r) { this.r = r; }
        public bool MoveNext() { return ++i < r.count; }
        public object Current { get { return r.start + i; } }
        public void Reset() { i = -1; }
    }
}

class App
{
    static void Main()
    {
        foreach (int x in new Range(3, 4))
        {
            Console.Write(x + " ");
        }
        Console.WriteLine();
    }
}
