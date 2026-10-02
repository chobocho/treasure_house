// 슬라이드 p10-v9-with-null — null 에 with 를 쓰면, C# 9.0
using System;

record Point(int X, int Y);

class App
{
    static Point Find(bool ok) => ok ? new Point(1, 2) : null;

    static void Main()
    {
        Point p = Find(true) with { Y = 5 };
        Console.WriteLine(p);
        try
        {
            Point q = Find(false) with { Y = 5 };   // clone on null
            Console.WriteLine(q);
        }
        catch (NullReferenceException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
