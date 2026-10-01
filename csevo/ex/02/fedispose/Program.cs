// 슬라이드 p2-v1_2-foreachdispose — foreach 와 Dispose, C# 1.2
using System;
using System.Collections;

class Lines : IEnumerable
{
    public IEnumerator GetEnumerator() { return new Reader(); }

    class Reader : IEnumerator, IDisposable
    {
        int i;
        public bool MoveNext() { return ++i <= 3; }
        public object Current { get { return "line" + i; } }
        public void Reset() { i = 0; }
        public void Dispose() { Console.WriteLine("  Dispose"); }
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine("to the end:");
        foreach (string s in new Lines()) Console.WriteLine("  " + s);

        Console.WriteLine("break:");
        foreach (string s in new Lines())
        {
            Console.WriteLine("  " + s);
            break;
        }

        Console.WriteLine("exception:");
        try
        {
            foreach (string s in new Lines())
                throw new ApplicationException("stop at " + s);
        }
        catch (ApplicationException e)
        {
            Console.WriteLine("  caught: " + e.Message);
        }
    }
}
