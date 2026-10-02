// 슬라이드 p10-v9-init-readonly — init 과 readonly 필드, C# 9.0
using System;

public class Person
{
    protected readonly string firstName = "<unknown>";

    public string FirstName
    {
        get => firstName;
        init => firstName = value
            ?? throw new ArgumentNullException(nameof(FirstName));
    }
}

#if BAD
public class Employee : Person
{
    public string Nick
    {
        init => firstName = value;           // base's readonly field
    }
}
#endif

class App
{
    static void Main()
    {
        Console.WriteLine(new Person().FirstName);
        Console.WriteLine(new Person { FirstName = "Mads" }.FirstName);
        try { new Person { FirstName = null }.ToString(); }
        catch (ArgumentNullException e)
        {
            Console.WriteLine(e.ParamName);
        }
    }
}
