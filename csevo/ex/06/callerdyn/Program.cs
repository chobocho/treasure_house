// 슬라이드 p6-v5-caller-dyn — dynamic 호출과 쿼리 식, C# 5.0
using System;
using System.Runtime.CompilerServices;

class Seq
{
    public string Who([CallerMemberName] string m = "(default)",
        [CallerLineNumber] int line = -1)
    {
        return m + " line " + line;
    }

    // Query pattern: 'where' in a query becomes a call to this.
    public Seq Where(Func<int, bool> p,
        [CallerMemberName] string m = "(default)",
        [CallerLineNumber] int line = -1)
    {
        Console.WriteLine("Where   <- " + m + " line " + line);
        return this;
    }
    public Seq Select(Func<int, int> f) { return this; }
}

class App
{
    static void Main()
    {
        Seq s = new Seq();
        Console.WriteLine("static  <- " + s.Who());
        dynamic d = s;
        Console.WriteLine("dynamic <- " + d.Who());
        Seq q = from x in s
                where x > 0
                select x;
    }
}
