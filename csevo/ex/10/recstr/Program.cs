// 슬라이드 p10-v9-rec-tostring — 컴파일러가 만드는 ToString, C# 9.0
using System;

record Person(string FirstName, string LastName, string[] ChildNames);
record Line(Point From, Point To);
record Point(int X, int Y);
record Empty;
record Tagged(string Name)
{
    public int Count;                     // public field: printed
    private int secret = 7;               // private: not printed
    public static int Total = 0;          // static: not printed
    public int Secret() => secret;
}

class App
{
    static void Main()
    {
        string[] kids = { "Ann" };
        Console.WriteLine(new Person("Nancy", "Davolio", kids));
        Console.WriteLine(new Line(new Point(0, 0), new Point(3, 4)));
        Console.WriteLine(new Person(null, "", null));
        Console.WriteLine(new Empty());
        Console.WriteLine(new Tagged("t") { Count = 2 });
    }
}
