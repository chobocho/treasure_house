// 슬라이드 p12-v11-sa-factory — 수학 밖의 쓰임: 팩터리, C# 11.0
using System;
using System.Collections.Generic;

interface IShape<TSelf> where TSelf : IShape<TSelf>
{
    static abstract string Kind { get; }
    static abstract TSelf Create(double size);    // a "constructor"
    double Area { get; }
}

class Square : IShape<Square>
{
    double s;
    Square(double size) => s = size;              // private ctor
    public static string Kind => "square";
    public static Square Create(double size) => new Square(size);
    public double Area => s * s;
}

class Circle : IShape<Circle>
{
    double r;
    Circle(double size) => r = size / 2;
    public static string Kind => "circle";
    public static Circle Create(double size) => new Circle(size);
    public double Area => Math.Round(Math.PI * r * r, 3);
}

class App
{
    // new() could only call a public parameterless constructor
    static List<T> Make<T>(params double[] sizes) where T : IShape<T>
    {
        var list = new List<T>();
        foreach (double d in sizes) list.Add(T.Create(d));
        Console.Write(T.Kind + ":");
        foreach (T t in list) Console.Write(" " + t.Area);
        Console.WriteLine();
        return list;
    }

    static void Main()
    {
        Make<Square>(1, 2, 3);
        Make<Circle>(2, 4);
    }
}
