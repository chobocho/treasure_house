// 슬라이드 p13-v12-pc-semi — 몸체 대신 세미콜론, C# 12.0
using System;

class Shape(string kind) { public string Kind => kind; }
class Circle(double r) : Shape($"circle {r}");   // parameters only
class Marker;                                    // no list either
struct Unit;
interface IEmpty;
enum Nothing;

class App
{
    static void Main()
    {
        Console.WriteLine(new Circle(1.5).Kind);
        Console.WriteLine(new Marker().GetType().Name);
        Console.WriteLine(default(Unit).GetType().Name);
        Console.WriteLine(typeof(IEmpty).IsInterface);
        Console.WriteLine(Enum.GetNames(typeof(Nothing)).Length);
    }
}
