// 슬라이드 p7-v6-eb-void — void 메서드의 식 본문, C# 6.0
using System;

class Counter
{
    int count;

    // void: the expression must be one that can stand as a statement
    public void Hit() => count++;
    public void Show() => Console.WriteLine("count = " + count);

#if BAD
    public void Sum() => 1 + 2;
#endif
#if BAD2
    public void Log(string s) => if (s != null) Console.WriteLine(s);
#endif
}

class Program
{
    static void Main()
    {
        Counter c = new Counter();
        c.Hit();
        c.Hit();
        c.Show();
    }
}
