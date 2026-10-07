// 슬라이드 p16-cp-at — @ 로 옛 이름을 지키기, C# 14
using System;

class @required { }       // CS9029 without @
class @extension { }      // CS9306 without @
class @partial { }
class token { }           // CS8981 at -warn:7 (no @)

class Program
{
    int field = 7;
    int Old { get { return @field; } }  // the member, not field

    static @partial Make() { return new @partial(); }

    static void Main()
    {
        Console.WriteLine(new Program().Old);
        Console.WriteLine(Make());
        Console.WriteLine(new @required());
        Console.WriteLine(new @extension());
        Console.WriteLine(new token());
    }
}
