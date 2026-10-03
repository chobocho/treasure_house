// 슬라이드 p11-v10-wi-generic — 형식 매개변수에 with, C# 10.0
using System;

interface IHasId { int Id { get; set; } }

struct Item : IHasId { public int Id { get; set; } }

class App
{
    static T ByStruct<T>(T x, int id) where T : struct, IHasId
        => x with { Id = id };              // T is known to be a struct

#if BAD
    static T ByAny<T>(T x, int id) where T : IHasId
        => x with { Id = id };              // could be a class
#endif

    static void Main()
    {
        var a = new Item { Id = 1 };
        var b = ByStruct(a, 2);
        Console.WriteLine(a.Id + " " + b.Id);
    }
}
