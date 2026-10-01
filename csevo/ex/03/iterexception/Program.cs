// 슬라이드 p3-v2-iterator-exception — 예외 뒤의 반복기, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Risky()
    {
        yield return 1;
        throw new InvalidOperationException("boom");
    }

    static void Main()
    {
        IEnumerator<int> e = Risky().GetEnumerator();
        Console.WriteLine(e.MoveNext() + " " + e.Current);
        try
        {
            e.MoveNext();                 // the exception surfaces here
        }
        catch (InvalidOperationException ex)
        {
            Console.WriteLine("caught " + ex.Message);
        }
        Console.WriteLine(e.MoveNext()); // state 'after': just false
    }
}
