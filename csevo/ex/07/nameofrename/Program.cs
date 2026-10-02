// 슬라이드 p7-v6-nameof-rename — 이름을 바꾼 뒤의 문자열, C# 6.0
using System;

class Users
{
    // the parameter used to be called "name"; it was renamed
    public static void AddOld(string userName)
    {
        if (userName == null)
            throw new ArgumentNullException("name");     // stale
    }

    public static void AddNew(string userName)
    {
        if (userName == null)
            throw new ArgumentNullException(nameof(userName));
    }
}

class App
{
    static void Main()
    {
        try { Users.AddOld(null); }
        catch (ArgumentNullException e)
        { Console.WriteLine("old: " + e.ParamName); }
        try { Users.AddNew(null); }
        catch (ArgumentNullException e)
        { Console.WriteLine("new: " + e.ParamName); }
        // the runtime's own name for the parameter
        Console.WriteLine("real: " + typeof(Users)
            .GetMethod("AddOld").GetParameters()[0].Name);
    }
}
