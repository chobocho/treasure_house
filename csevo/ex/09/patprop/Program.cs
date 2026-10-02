// 슬라이드 p9-v8-proppat — 속성 패턴, C# 8.0
using System;

class Address
{
    public string Country { get; set; }
    public string City { get; set; }
}

class App
{
    // the rule lives outside Address: it changes more often
    static decimal Shipping(Address a, decimal price) => a switch
    {
        { Country: "KR", City: "Jeju" } => 6000m,
        { Country: "KR" } => 3000m,
        { Country: "JP" } => 12000m + price * 0.01m,
        _ => 30000m,
    };

    static void Main()
    {
        var list = new[]
        {
            new Address { Country = "KR", City = "Seoul" },
            new Address { Country = "KR", City = "Jeju" },
            new Address { Country = "JP", City = "Osaka" },
            new Address { Country = "US", City = "Austin" },
        };
        foreach (Address a in list)
            Console.WriteLine("{0}/{1,-6} {2,8:0}",
                a.Country, a.City, Shipping(a, 50000m));
    }
}
