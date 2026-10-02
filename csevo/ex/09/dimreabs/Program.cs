// 슬라이드 p9-v8-dim-reabs — 재추상화, C# 8.0
using System;

interface IShape
{
    string Describe() => "a shape";
}

// for polygons the default is too vague: take it away again
interface IPolygon : IShape
{
    int Sides { get; }
    abstract string IShape.Describe();
}

class Square : IPolygon
{
    public int Sides => 4;
    public string Describe() => "a square, " + Sides + " sides";
}

#if BAD
class Triangle : IPolygon { public int Sides => 3; }
#endif

class App
{
    static void Main()
    {
        IShape s = new Square();
        Console.WriteLine(s.Describe());
    }
}
