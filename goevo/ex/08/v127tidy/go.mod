module ex/08/v127tidy

go 1.27

require example.com/alpha v0.0.0

// added later, by hand
require example.com/beta v0.0.0

replace example.com/alpha => ./alpha

replace example.com/beta => ./beta
