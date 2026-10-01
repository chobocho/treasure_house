// 슬라이드 p2-v1_2-desugar — foreach 를 손으로 풀어 쓰면, C# 1.2
using System;
using System.Collections;

class Reader : IEnumerator, IDisposable
{
    int i;
    public bool MoveNext() { return ++i <= 3; }
    public object Current { get { return "line" + i; } }
    public void Reset() { i = 0; }
    public void Dispose() { Console.WriteLine("  Dispose"); }
}

class App
{
    static void Main()
    {
        Console.WriteLine("no finally (what 1.0 lacked):");
        IEnumerator e = new Reader();
        while (e.MoveNext())
        {
            string s = (string)e.Current;
            Console.WriteLine("  " + s);
            break;
        }

        Console.WriteLine("with finally (1.2 and later):");
        IEnumerator e2 = new Reader();
        try
        {
            while (e2.MoveNext())
            {
                string s = (string)e2.Current;
                Console.WriteLine("  " + s);
                break;
            }
        }
        finally
        {
            IDisposable d = e2 as IDisposable;   // a run-time test
            if (d != null) d.Dispose();
        }
    }
}
