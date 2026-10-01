// 슬라이드 p3-v2-iterator-getenumerator — IEnumerator 반복기, C# 2.0
using System;
using System.Collections.Generic;

class Countdown
{
    int from;
    public Countdown(int from) { this.from = from; }

    public IEnumerator<int> GetEnumerator()   // an iterator, too
    {
        for (int i = from; i > 0; i--)
        {
            yield return i;
        }
    }
}

class App
{
    static void Main()
    {
        foreach (int x in new Countdown(3))   // finds GetEnumerator
        {
            Console.Write(x + " ");
        }
        Console.WriteLine();
        IEnumerator<int> e = new Countdown(2).GetEnumerator();
        while (e.MoveNext()) Console.Write(e.Current + " ");
        Console.WriteLine();
    }
}
